#!/bin/bash

# Author: Alex Shteinikov

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR'/../import_base'
rm -f *.csv

entries=( docs/mech_tweenk/*.csv )
for FILE in "${entries[@]}"; do
  NEWFILE="$(echo $FILE | sed -e 's/-Table 1//' | sed -e 's/.*\///' )"
  
  cp "$FILE" "./"$NEWFILE
  echo "Ok... "$NEWFILE
done

entries=( docs/actions/*.csv )
for FILE in "${entries[@]}"; do
  NEWFILE="$(echo $FILE | sed -e 's/-Table 1//' | sed -e 's/.*\///' )"

  cp "$FILE" "./"$NEWFILE
  echo "Ok... "$NEWFILE
done