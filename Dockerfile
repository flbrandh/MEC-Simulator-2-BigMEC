FROM python:3.11

Copy . .

RUN apt-get update
RUN apt-get install -y jq moreutils
RUN python3 -m pip install --no-cache-dir --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# This command runs the simulator in headless mode (without visualization)
CMD ["python3", "./main.py", "--headless"]
