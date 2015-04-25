#!/bin/bash -

mkdir -p compact

SED='sed'

[[ $(uname) == "Darwin" ]] && SED='gsed'

for i in *.txt ; do
	cat $i | ${SED} -f compact.sed > compact/$i
done
