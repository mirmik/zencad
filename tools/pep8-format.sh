set -x

for file in ./**/*.py; do
  autopep8 --in-place "$file"
done

for file in ./**/**/*.py; do
  autopep8 --in-place "$file"
done