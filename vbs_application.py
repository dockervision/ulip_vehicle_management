import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import threading

class VehicleBookingSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vehicle Booking System")
        self.root.geometry("1000x700")  # Increased window size to accommodate new details

        # API Base URL (assuming local development)
        self.BASE_URL = "http://localhost:5000"

        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create left and right frames
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Time Range Selection
        self.create_time_range_section()

        # Containers List
        self.create_containers_section()

        # Container Details
        self.create_container_details_section()

        # Additional Details Section (initially hidden)
        self.create_additional_details_section()

    def create_time_range_section(self):
        # Time Range Frame
        time_frame = ttk.LabelFrame(self.left_frame, text="Time Range Selection")
        time_frame.pack(fill=tk.X, pady=10)

        # Start Time
        ttk.Label(time_frame, text="Start Time:").grid(row=0, column=0, padx=5, pady=5)
        self.start_time_entry = ttk.Entry(time_frame, width=25)
        self.start_time_entry.grid(row=0, column=1, padx=5, pady=5)
        self.start_time_entry.insert(0, ("2022-12-01 00:00:00"))

        # End Time
        ttk.Label(time_frame, text="End Time:").grid(row=0, column=2, padx=5, pady=5)
        self.end_time_entry = ttk.Entry(time_frame, width=25)
        self.end_time_entry.grid(row=0, column=3, padx=5, pady=5)
        self.end_time_entry.insert(0, ("2023-02-21 17:00:00"))

        # Fetch Containers Button
        ttk.Button(time_frame, text="Fetch Containers", command=self.fetch_containers).grid(row=0, column=4, padx=5, pady=5)

    def create_containers_section(self):
        # Containers Frame
        containers_frame = ttk.LabelFrame(self.left_frame, text="Containers")
        containers_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Containers Treeview
        self.containers_tree = ttk.Treeview(containers_frame, 
            columns=('Container Number', 'Expected Arrival'), 
            show='headings'
        )
        self.containers_tree.heading('Container Number', text='Container Number')
        # self.containers_tree.heading('Booking Time', text='Booking Time')
        self.containers_tree.heading('Expected Arrival', text='Expected Arrival')
        self.containers_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bind selection event
        self.containers_tree.bind('<<TreeviewSelect>>', self.on_container_select)

    def create_container_details_section(self):
        # Container Details Frame
        details_frame = ttk.LabelFrame(self.left_frame, text="Container Details")
        details_frame.pack(fill=tk.X, pady=10)

        # Status Labels
        ttk.Label(details_frame, text="Container Number:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.container_number_label = ttk.Label(details_frame, text="")
        self.container_number_label.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(details_frame, text="Time Difference:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.time_diff_label = ttk.Label(details_frame, text="")
        self.time_diff_label.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # ttk.Label(details_frame, text="Delay:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        # self.delay_label = ttk.Label(details_frame, text="")
        # self.delay_label.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # OCR Update Button
        self.ocr_update_btn = ttk.Button(details_frame, text="Simulate OCR Update", 
                                       command=self.simulate_ocr_update, state=tk.DISABLED)
        self.ocr_update_btn.grid(row=3, column=0, columnspan=2, pady=10)

    def create_additional_details_section(self):
        # Additional Details Frame (Right Side)
        self.additional_frame = ttk.LabelFrame(self.right_frame, text="Additional Details")
        self.additional_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        # Event Name
        ttk.Label(self.additional_frame, text="Event Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.event_name_label = ttk.Label(self.additional_frame, text="")
        self.event_name_label.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Current Location
        ttk.Label(self.additional_frame, text="Current Location:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.current_location_label = ttk.Label(self.additional_frame, text="")
        self.current_location_label.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Latitude
        ttk.Label(self.additional_frame, text="Latitude:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.latitude_label = ttk.Label(self.additional_frame, text="")
        self.latitude_label.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Longitude
        ttk.Label(self.additional_frame, text="Longitude:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.longitude_label = ttk.Label(self.additional_frame, text="")
        self.longitude_label.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Initially hide the additional frame
        self.additional_frame.pack_forget()

    def fetch_containers(self):
        # Clear previous results
        for i in self.containers_tree.get_children():
            self.containers_tree.delete(i)

        # Get time range
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()

        try:
            # Make API call
            response = requests.get(f"{self.BASE_URL}/api/containers", 
                                 params={'start_time': start_time, 'end_time': end_time})
            
            if response.status_code == 200:
                containers = response.json()
                for container in containers:
                    self.containers_tree.insert('', 'end', values=(
                        container['container_number'], 
                        container['booking_time'], 
                        container['expected_arrival_time']
                    ))
            else:
                messagebox.showerror("Error", f"Failed to fetch containers: {response.text}")
        
        except requests.RequestException as e:
            messagebox.showerror("Network Error", str(e))

    def on_container_select(self, event):
        # Get selected container
        selected_item = self.containers_tree.selection()
        if not selected_item:
            return

        # Get container number
        container_number = self.containers_tree.item(selected_item)['values'][0]
        
        # Enable OCR Update button
        self.ocr_update_btn.config(state=tk.NORMAL)

        # Fetch container status in a separate thread
        threading.Thread(target=self.fetch_container_status, args=(container_number,), daemon=True).start()

    def fetch_container_status(self, container_number):
        try:
            # Make API call
            response = requests.get(f"{self.BASE_URL}/api/container/status/{container_number}")
            
            if response.status_code == 200:
                status = response.json()
                # Get container details from API
                auth_token = self.get_auth_token()
                if auth_token:
                    container_info = self.get_container_info(container_number, auth_token)
                    if container_info:
                        container_details = self.extract_container_details(container_info)
                        status['container_details'] = container_details
                
                # Update UI (use after to ensure thread-safe update)
                self.root.after(0, self.update_container_status, status)
            else:
                messagebox.showerror("Error", f"Failed to fetch container status: {response.text}")
        
        except requests.RequestException as e:
            messagebox.showerror("Network Error", str(e))

    def get_auth_token(self):
        """Get authentication token from ULIP API"""
        url = "https://www.ulipstaging.dpiit.gov.in/ulip/v1.0.0/user/login"
        payload = {
            "username": "docker_usr",
            "password": "docker@28112024"
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get('error') == 'false' and data.get('code') == '200':
                return f"Bearer {data['response']['id']}"
            return None
        except Exception:
            return None

    def get_container_info(self, container_number, auth_token):
        """Get container information from ULIP API"""
        url = "https://www.ulipstaging.dpiit.gov.in/ulip/v1.0.0/LDB/01"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': auth_token
        }
        payload = {"containerNumber": container_number}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def extract_container_details(self, container_data):
        """Extract relevant container details from API response"""
        try:
            if 'response' in container_data and container_data['response']:
                first_response = container_data['response'][0]
                last_event = first_response.get('response', {}).get('eximContainerTrail', {}).get('last_event', [{}])[0]
                
                return {
                    'eventname': last_event.get('eventname', 'N/A'),
                    'currentlocation': last_event.get('currentlocation', 'N/A'),
                    'latitude': last_event.get('latitude', 'N/A'),
                    'longitude': last_event.get('longitude', 'N/A')
                }
            return None
        except Exception:
            return None

    def update_container_status(self, status):
        # Update container details
        self.container_number_label.config(text=status.get('container_number', 'N/A'))
        
        # Update Time Difference
        time_diff = status.get('time_difference')
        if time_diff is not None:
            if time_diff < 0:
                self.time_diff_label.config(text="On-time", foreground="green")
                self.ocr_update_btn.config(state=tk.NORMAL)  # Enable button when On-time
                self.additional_frame.pack_forget()  # Hide additional details
            else:
                self.time_diff_label.config(text=f"Delayed: {time_diff:.2f} min", foreground="red")
                self.ocr_update_btn.config(state=tk.DISABLED)  # Disable button when Delayed
                
                # Update additional details
                container_details = status.get('container_details', {})
                self.event_name_label.config(text=container_details.get('eventname', 'N/A'))
                self.current_location_label.config(text=container_details.get('currentlocation', 'N/A'))
                self.latitude_label.config(text=container_details.get('latitude', 'N/A'))
                self.longitude_label.config(text=container_details.get('longitude', 'N/A'))
                
                # Show additional details frame
                self.additional_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        else:
            self.time_diff_label.config(text="N/A", foreground="black")
            self.ocr_update_btn.config(state=tk.DISABLED)  # Disable button when N/A
            self.additional_frame.pack_forget() 

    def simulate_ocr_update(self):
        # Get selected container
        selected_item = self.containers_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a container")
            return

        container_number = self.containers_tree.item(selected_item)['values'][0]

        try:
            # Make OCR update API call
            response = requests.post(f"{self.BASE_URL}/api/ocr/update", 
                                  json={'container_number': container_number})
            
            if response.status_code == 200:
                messagebox.showinfo("Success", f"Container ({container_number}) housed within the port facility!")
                # Refresh container status
                self.fetch_container_status(container_number)
            else:
                messagebox.showerror("Error", f"Failed to update OCR: {response.text}")
        
        except requests.RequestException as e:
            messagebox.showerror("Network Error", str(e))

def main():
    root = tk.Tk()
    app = VehicleBookingSystemApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()