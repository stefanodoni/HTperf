#!/bin/sh

for f in stat* trace* web* db* client* ; do
	rm /tmp/$f
done
