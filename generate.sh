#!/bin/sh

mkdir -p compact

for i in *.txt ; do
	cat $i | gsed -f compact.sed > compact/$i
done
