#!/usr/bin/bash

input_folder=$1
output_folder=${input_folder}_output

book_id=$(calibredb search --library-path piano "series:partition")

rm -Rf $output_folder
calibredb export --formats mscz --template "{series_index:0>2s} - {title}" \
 --single-dir \
 --dont-save-cover \
 --dont-write-opf \
 --library-path $input_folder \
 --to-dir $output_folder \
 $book_id


# Find missing series number

# Convert to midi

# Add blank midi files for sd card
