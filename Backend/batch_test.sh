#!/bin/bash

for i in {1..10}; do
  echo "Run #$i"
  python3 agent.py test_river_bridge
done
