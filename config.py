from dotenv import load_dotenv
load_dotenv() 
import os
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip().isdigit()]
