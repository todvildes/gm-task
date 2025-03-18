#!/bin/bash
set -e

# Configuration
LAMBDA_PACKAGE_DIR="lambda_package"
ZIP_FILE="lambda_deployment_package.zip"
APP_DIR="app"
REQUIREMENTS_FILE="requirements.txt"
TMP_REQUIREMENTS="tmp_requirements.txt"

# Clean up previous builds
rm -rf $LAMBDA_PACKAGE_DIR $ZIP_FILE
mkdir -p $LAMBDA_PACKAGE_DIR

# Copy all Python files to the root level (flattening the structure)
echo "Copying app files to root level of package..."
cp $APP_DIR/*.py $LAMBDA_PACKAGE_DIR/

# Create temporary requirements file without localstack and testing packages
echo "Creating temporary requirements file without problematic packages..."
grep -v -E "localstack|pytest" $REQUIREMENTS_FILE > $TMP_REQUIREMENTS

# Install dependencies with Lambda-specific flags
echo "Installing dependencies from filtered requirements..."
pip install -r $TMP_REQUIREMENTS \
    --platform manylinux2014_x86_64 \
    --target $LAMBDA_PACKAGE_DIR \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade

echo "Note: Skipping localstack and pytest as they're not needed in the Lambda environment"

# Remove unnecessary files to reduce package size
echo "Cleaning up unnecessary files..."
find $LAMBDA_PACKAGE_DIR -name '__pycache__' -type d -exec rm -rf {} +
find $LAMBDA_PACKAGE_DIR -name '*.pyc' -delete
find $LAMBDA_PACKAGE_DIR -name '.pytest_cache' -type d -exec rm -rf {} +
find $LAMBDA_PACKAGE_DIR -name '.git' -type d -exec rm -rf {} +
find $LAMBDA_PACKAGE_DIR -name 'tests' -type d -exec rm -rf {} +
find $LAMBDA_PACKAGE_DIR -name '*.dist-info' -type d -exec rm -rf {} +
find $LAMBDA_PACKAGE_DIR -name '*.egg-info' -type d -exec rm -rf {} +

# Create zip file
echo "Creating deployment package..."
cd $LAMBDA_PACKAGE_DIR
zip -r ../$ZIP_FILE .
cd ..

# Clean up temp file
rm $TMP_REQUIREMENTS

echo "Created Lambda deployment package: $ZIP_FILE"
echo "Package size: $(du -h $ZIP_FILE | cut -f1)" 
