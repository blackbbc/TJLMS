#!/bin/bash
rm -rf src/static/*
rm -f src/templates/*
cp -R ../TJLMS-FE2/dist/static/* src/static/
cp ../TJLMS-FE2/dist/index.html src/templates/
