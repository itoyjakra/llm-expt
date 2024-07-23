#!/bin/bash

echo "Executing create_pkg.sh..."

cd $path_cwd
dir_name=lambda_dist_pkg/
mkdir $dir_name

# Create and activate virtual environment...
virtualenv -p $runtime env_$function_name
source $path_cwd/env_$function_name/bin/activate

# Instal python dependencies...
FILE=$path_cwd/lambda_functions/requirements.txt

if [ -f "$FILE" ]; then
  echo "Installing dependencies from requirements.txt"
  pip install -r "$FILE"
else
  echo "Error: requirements.txt does not exist!"
fi

# Deactivate virtual environment...
deactivate

# Create deployment package...
echo "Creating deployment package..."
cd env_$function_name/lib/$runtime/site-packages/
cp -r . $path_cwd/$dir_name
cp -r $path_cwd/lambda_functions/ $path_cwd/$dir_name

# Removing virtual environment folder...
echo "Removing virtual environment folder..."
rm -rf $path_cwd/env_$function_name

echo "Finished script execution!"
