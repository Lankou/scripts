#!/bin/bash
[ -z $1 ] && echo "Usage: $(basename $0) [file]" && exit 0

#ext=${1#.}
ext=$(echo $1 | awk -F . '{print $NF}')
savetarget=~/Desktop

for s in 1 2 3
do
  echo $1 | grep -E '\.' &> /dev/null
  if [ $? -eq 0 ]; then
  	git show :$s:$1 > $savetarget/$s.$ext
  else
    git show :$s:$1 > $savetarget/$s
  fi
done

