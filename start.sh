
# test python 3.10 installation
python3.10 --version
if [ $? -ne 0 ]; then
    echo "Python 3.10 is not installed."
    exit 1
else
    echo "Python 3.10 founded."
fi

# check virtual environment
if [ -d "venv" ]; then
    echo "Virtual environment 'venv' exists."
else
    echo "Creating virtual environment 'venv'."
    python3.10 -m venv venv
fi

# activate virtual environment
source venv/bin/activate

# install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping dependency installation."
fi

# start the application
echo "Starting the application."
python -m zencad


