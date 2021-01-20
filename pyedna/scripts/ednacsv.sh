#!/usr/bin/env bash
#
# Export eDNA data records to CSV. From each eDNA data file, the following
# CSV files are produced:
#
#    - samples_$ID.csv
#    - results_$ID.csv
#    - depth_$ID.csv
#    - battery_$ID.csv
#
# This script requires jq (https://stedolan.github.io/jq/) to process the
# JSON data records.
#

# jq is required
set -e
type jq >&2

infile="$1"
[[ -z $infile ]] && {
    echo "Missing input file" 2>&1
    echo "Usage: ${0##*/} infile" 1>&2
    exit 1
}

# Extract the deployment ID from the filename
base="${infile##*/}"
base="${base%.*}"
id=$(cut -f2 -d_ <<<"$base")

outfile="sample_${id}.csv"
echo -n "Creating $outfile ... "
echo "time,sample,elapsed,amount,pr,depth" > $outfile
jq -r -M \
   '{t: .t, ev: (.event / "."), data: .data}|select( .ev[0] == "sample")|[.t, .ev[1], .data.elapsed, .data.amount, .data.pr, .data.depth]|@csv' $infile >> $outfile
echo "done"

outfile="result_${id}.csv"
echo -n "Creating $outfile ... "
echo "time,sample,elapsed,vwater,vethanol,overpressure,deptherror" > $outfile
jq -r -M \
   '{t: .t, ev: (.event / "."), data: .data}|select( .ev[0] == "result")|[.t, .ev[1], .data.elapsed, .data.vwater, .data.vethanol, .data.overpressure, .data.deptherror // false]|@csv' $infile >> $outfile
echo "done"

outfile="battery_${id}.csv"
echo -n "Creating $outfile ... "
echo "time,battery,voltage,current,soc" > $outfile
jq -r -M \
   '{t: .t, ev: (.event / "-"), data: .data}|select( .ev[0] == "battery")|[.t, .ev[1], .data.v, .data.a, .data.soc]|@csv' $infile >> $outfile
echo "done"

outfile="depth_${id}.csv"
echo -n "Creating $outfile ... "
echo "time,depth" > $outfile
jq -r -M \
   'select( .event == "depth")|[.t, .data.depth]|@csv' $infile >> $outfile
echo "done"
