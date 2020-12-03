#!/usr/bin/env bash
#
# Walk the user through creating an eDNA deployment configuration
# file then start the deployment.
#

: ${CFGDIR=$HOME/config}

export PATH=$PATH:$HOME/.local/bin

prompt ()
{
    local q default ans
    q="$1"
    default="$2"
    if [[ -z "$default" ]]; then
        read -p "${q}? " ans
        echo "$ans"
    else
        read -p "${q} [$default]? " ans
        echo "${ans:-$default}"
    fi
}

UNIT="runedna@deploy.service"

if systemctl --user --quiet is-active "$UNIT"; then
    ans=$(prompt "Abort active deployment (y/n)" "n")
    case "$ans" in
        n|N|no)
            exit 0
            ;;
    esac
    systemctl --user stop "$UNIT"
fi

mkdir -p $CFGDIR

trap "echo 'Aborting'; exit 1" 1 2 3 15

depths=()
for i in {1..3}; do
    depths[i]=$(prompt "Sample $i depth (dbar)")
done

seekerr=$(prompt "Allowed error when depth seeking (dbar)" 2)
deptherr=$(prompt "Allowed error when holding depth (dbar)" 2)
prrate=$(prompt "Pressure sampling rate (hz)" 4)
seektime=$(prompt "Maximum depth seek time (sec)" 1800)

cfgfile=$CFGDIR/deploy.cfg
echo "# Created: $(date +'%F %T')" > $cfgfile
cat<<EOF >> $cfgfile
[Deployment]
SeekErr = $seekerr
DepthErr = $deptherr
PrRate = $prrate
SeekTime = $seektime

EOF

for i in {1..3}; do
    echo "[Sample.$i]"
    echo "Depth=${depths[i]}"
done >> $cfgfile

resp=$(prompt "Adjust sample collection parameters (y/n)" "n")
case "$resp" in
    Y|y|yes)
        s_amount=$(prompt "Sample amount (liters)" "0.2")
        s_time=$(prompt "Sample time limit (secs)" "60")
        e_amount=$(prompt "Ethanol amount (liters)" "0.01")
        e_time=$(prompt "Ethanol time limit (secs)" "20")
        {
            echo "[Collect.Sample]"
            echo "Amount = $s_amount"
            echo "Time = $s_time"
            echo "[Collect.Ethanol]"
            echo "Amount = $e_amount"
            echo "Time = $e_time"
        } >> $cfgfile
    ;;
esac

echo -n "Starting deployment, standby ..."
if systemctl --user start "$UNIT"; then
    sleep 5
    if systemctl --user --quiet is-active "$UNIT"; then
        echo "done"
        exit 0
    else
        echo "FAILED"
        systemctl --user --no-pager -l status "$UNIT"
    fi
fi

exit 1
