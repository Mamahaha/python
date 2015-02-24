#!/bin/bash

hdfs dfs -mkdir /input
hdfs dfs -copyFromLocal The_Testament.txt /input/

hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -mapper ./mapper.py \
  -reducer ./reducer.py \
  -input /input/The_Testament.txt \
  -output /output

hdfs dfs -copyToLocal /output .
hdfs dfs -rm -r -f /input
hdfs dfs -rm -r -f /usr
hdfs dfs -rm -r -f /output
