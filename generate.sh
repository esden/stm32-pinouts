#!/bin/bash -

mkdir -p compact

SED='sed'

[[ $(uname) == "Darwin" ]] && SED='gsed'

for i in source/*.txt ; do
	echo "Converting to compact: " $(basename $i)
	cat $i | ${SED} -f compact.sed > compact/$(basename $i)
done
