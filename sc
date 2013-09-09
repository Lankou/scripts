#!/bin/bash
[ -z $1 ] && echo "Usage: $(basename $0) [file]" && exit 0

#ext=${1#.}
ext=$(echo $1 | awk -F . '{print $NF}')

for s in 1 2 3
do
  echo $ext | grep -E '\.'
  if [ $? -eq 0 ]; then
  	git show :$s:$1 > ~/Desktop/$s.$ext
  else
    git show :$s:$1 > ~/Desktop/$s
  fi
done

