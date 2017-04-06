#!/bin/bash
cd ../TJLMS-FE
git pull
cd ../TJLMS
cp ../TJLMS-FE/dist/main.js src/static/
cp ../TJLMS-FE/dist/style.css src/static/
cp ../TJLMS-FE/dist/vendor.css src/static/
cp ../TJLMS-FE/dist/vendor.js src/static/
cp ../TJLMS-FE/dist/index.html src/templates/
