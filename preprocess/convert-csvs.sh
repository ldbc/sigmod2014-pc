#!/bin/bash

set -e

# if the source encoding is already UTF-8, it's possible to do an in-place conversion
CSV_IN_DIR=$1
CSV_OUT_DIR=$2
SOURCE_ENCODING=${3:-utf-8}

echo "Starting preprocessing CSV files"

# based on the catalog in 'headers.txt',
# copy selected files, fix their encoding, and add headers
while read line; do
  IFS=' ' read -r -a array <<< $line
  FILENAME=${array[0]}
  HEADER=${array[1]}

  echo $FILENAME

  if [ ${SOURCE_ENCODING} != "utf-8" ]; then
    iconv -f ${SOURCE_ENCODING} -t utf-8 "${CSV_IN_DIR}/${FILENAME}.csv" > "${CSV_OUT_DIR}/${FILENAME}.csv"
  fi

  # use the simple combination of echo and cat for changing the header
  echo ${HEADER} | cat - <(tail -n +2 ${CSV_OUT_DIR}/${FILENAME}.csv) > tmpfile.csv && mv tmpfile.csv ${CSV_OUT_DIR}/${FILENAME}.csv
done < headers.txt

# replace labels with one starting with an uppercase letter
sed -i.bkp "s/|city$/|City/" "${CSV_OUT_DIR}/place.csv"
sed -i.bkp "s/|country$/|Country/" "${CSV_OUT_DIR}/place.csv"
sed -i.bkp "s/|continent$/|Continent/" "${CSV_OUT_DIR}/place.csv"

sed -i.bkp "s/|company|/|Company|/" "${CSV_OUT_DIR}/organisation.csv"
sed -i.bkp "s/|university|/|University|/" "${CSV_OUT_DIR}/organisation.csv"

# remove .bkp files
rm ${CSV_OUT_DIR}/*.bkp

echo "Finished preprocessing CSV files"
