import os
import time
from datetime import datetime
import csv
import io
import json
from utils import call_api_and_save_response
import requests
import ast
import base64

START_TIME = time.time()

def add_logs(text):
    today_logs = datetime.now().strftime("%y-%m-%d") + ".txt"
    file_name = os.path.join("logs", today_logs)
    with open(file_name, "a") as file:
        file.write(str(datetime.now()) + ": " + text + "\n")

def i_am_alive_checker():
    global START_TIME
    time_difference = time.time() - START_TIME
    # if time_difference > 600:
    #     url = 'https://hd624nqmkg.execute-api.eu-west-1.amazonaws.com/Prod/heartBeat'
    #     payload = {
    #         "device_id": "main_gate"
    #     }
    #     try:
    #         response = requests.post(url, json =payload)
    #         if response.status_code == 200:
    #             print("AWS notified successfully!")
    #         else:
    #             print("Failed to notify AWS. Status Code: {response.status_code}, Response: {response.text}")
    #     except Exception as e:
    #         print(f"Error notifying AWS: {e}")

            
    if time_difference > 3600:
        add_logs("Watcher is still alive!!!")
        START_TIME = time.time()


def generate_filename():
    # Get the current date
    today = datetime.now()
    
    # Format the date as Year-Month-Day
    formatted_date = today.strftime("%y-%m-%d")

    # Generate the file name
    file_name = f"all_data_{formatted_date}.csv"
    
    return file_name



def convert_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            # Read the image file in binary mode and encode it to Base64
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_string
    except FileNotFoundError:
        print(f"Error: File not found at path {image_path}")
        return None
    except Exception as e:
        print(f"Error converting image to Base64: {str(e)}")
        return None
        

def check_file_modification(file_path, last_mod_time):

    # Predefined keys that you want to send to the API
   

    try:
        # Get the current modification time
        current_mod_time = os.path.getmtime(file_path)
        if current_mod_time != last_mod_time:
            if last_mod_time != 0:
                print("The file has been modified.")
                print(f"{file_path}")
                add_logs("The file has been modified.")
                start = time.perf_counter()
                last_item = get_last_item()
                end = time.perf_counter()
                elapsed = end - start
                print(f'Time taken to identify plate: {elapsed:.6f} seconds')
                start1 = time.perf_counter()
                data_found = check_lp_against_available_ones(last_item)
                # camera_names =last_item["file"].split("/") 
                            #I added this
                end1 = time.perf_counter()
                elapsed1 = end1 - start1
                print(f"plate Compare time: {elapsed1:.6f} seconds")
                #data_found = check_lp_against_available_ones("gf22123")
                if data_found and last_item["orientation"][0]["orientation"]=="Front" :
                    start2 = time.perf_counter()
                    open_gate(last_item["file"].split("/")[1])
                    end2 = time.perf_counter()
                    elapsed2 = end2 - start2
                    print(f"Time taken to open gate: {elapsed2:.6f} seconds")
                #for item in last_item:
                  # log_entry_in_app({"model_make": item["model_make"],  "color": last_item["color"]})
               
                end3 = time.perf_counter()
                elapsed3 = end3 - start
                print(f'Time taken: {elapsed3:.6f} seconds')
                add_logs(f"Time taken:{elapsed3}s")
                
                
            return current_mod_time
        
        else:
            #print("No changes detected.")
            #add_logs("No changes detected.")
            return last_mod_time
        #Time=time.time()-START_TIME
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        #add_logs("File not found. Please check the file path.")
        return last_mod_time



def get_last_item():
    try:
        file_path = generate_filename()
        returnable_item = ""
        changed = False

        # Step 1: Clean the file by removing rows with NULL bytes
        cleaned_lines = []
        with open(file_path, 'rb') as infile:
            for line in infile:
                if b'\x00' not in line:  # Skip lines with NULL bytes
                    cleaned_lines.append(line)
        with open(file_path, 'rb') as original_file:
            original_content = original_file.readlines()

        # Only overwrite if the cleaned content differs from the original
        if cleaned_lines != original_content:
     # Step 2: Only overwrite the file if there were changes
            with open(file_path, 'wb') as outfile:
                outfile.writelines(cleaned_lines)

        # Step 3: Read the cleaned file
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                returnable_item = row  # Get the last item

        return returnable_item

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def log_entry_in_app(item):
    try:
        api_url = 'https://hd624nqmkg.execute-api.eu-west-1.amazonaws.com/Prod/grantAccessToVisitor'
        response = requests.post(api_url, json=item)
        print("The response for updating the app is ", response)
        print("The response text " + str(response.text))
        add_logs("The response for updating the app is " + str(response))
        return response
    except Exception as e:
        print("Error in sending log entry to app")
        add_logs("Error in sending log entry to app")
    

def check_lp_against_available_ones(lp):
    with open('api_response.txt', 'r') as file:
        data = json.load(file)

    for item in data:
        item_i_want_to_use = item["license_plate"].replace(" ", "").replace("-", "").lower()
        if item_i_want_to_use == lp["plate"]:
            print("License plate "+lp["plate"] +" found in the file.")
            add_logs("License plate "+lp["plate"] +" found in the file.")
            lp["model_make"] = ast.literal_eval(lp["model_make"])
            lp["color"] = ast.literal_eval(lp["color"])
            lp["direction"] = ast.literal_eval(lp["direction"]) if lp.get("direction") else ""
            lp["orientation"] = ast.literal_eval(lp["orientation"])
            item["make"] = lp["model_make"][0]["make"]
            item["model"] = lp["model_make"][0]["model"]
            item["color"] = lp["color"][0]["color"]
            item["orientation"] = lp["orientation"][0]["orientation"]
            item["direction"] = lp["direction"] 
            #item["imagebytes"] = convert_image_to_base64(lp["file"].lstrip("/"))
            #print(item["imagebytes"])
            
            if lp["model_make"][0]["score"]  < 0.5:
                item["make"] = ""
                item["model"] = ""
                print("make and model could be wrong")
            if lp["color"][0]["score"] < 0.5:   
                item["color"] = ""
                print("color could be wrong")
               #Send orient and direct to API. car is has left or entered if the orient is rear and direct is less than 300.
            #add_logs(f"the first entry into the app is {item}")
            add_logs("The file is " + lp["file"])
            camera_names = lp["file"].split("/")
            add_logs("Camera names are " + str(camera_names))
            item["camera_name"] = camera_names[1]
            add_logs("camera name is " + str(item["camera_name"]))
            if "camera-2" in item["camera_name"]:
                print("Logging entry in app")
            add_logs("Logging entry in app")
            log_entry_in_app(item)
           
            return True
    
    api_url = 'https://hd624nqmkg.execute-api.eu-west-1.amazonaws.com/Prod/getAllowedLicensePlatesWithThePeople?estate_id=EstateduITC-5632'  # Replace with your API URL
    file_name = 'api_response.txt'
    call_api_and_save_response(api_url, file_name)

    with open('api_response.txt', 'r') as file:
        data = json.load(file)

    for item in data:
        item_i_want_to_use = item["license_plate"].replace(" ", "").replace("-", "").lower()
        if item_i_want_to_use == lp["plate"]:
            print(f"License plate "+lp["plate"] +"found in the file.")
            add_logs(f"License plate "+lp["plate"] +" found in the file.")
            log_entry_in_app(item)
            return True

    print(f"License plate "+lp["plate"] +" not found in the file.")
    add_logs(f"License plate "+lp["plate"] +" not found in the file.")
    return False



def open_gate(data):
    
    try:
        print("Trying to open the gate")
        add_logs("Trying to open the gate")
        url = "http://156.0.234.156:5000/openGate"
        start4 = time.perf_counter()
        response = requests.post(url, json=data)        
        end4 = time.perf_counter()
        elapsed4 = end4 - start4
        print(response)
        print(f'Time taken: {elapsed4:.6f} seconds')
        print("Open gate")
        add_logs("The response from trying to open gate is " + str(response))
        add_logs("Response content:" + str(response.text))       
         
    except Exception as e:
        print("Had an issue opening gate")
        add_logs("Had an issue opening gate")



def main():
    
    last_mod_time = 0 
    while True:
        file_path = generate_filename()
        # Initialize with 0 to check for the first time
        last_mod_time = check_file_modification(file_path, last_mod_time)
        i_am_alive_checker()
        time.sleep(1)  # Wait for 1 second before checking again

if __name__ == "__main__":
    main()

