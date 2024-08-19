#!/bin/bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m' # No Color

# The sentence to display
SENTENCE="The quick brown fox jumps over the lazy dog"

# Split the sentence into words
WORDS=($SENTENCE)

# Display each word in a different color
echo -e "${RED}${WORDS[0]} ${GREEN}${WORDS[1]} ${YELLOW}${WORDS[2]} ${BLUE}${WORDS[3]} ${MAGENTA}${WORDS[4]} ${CYAN}${WORDS[5]} ${WHITE}${WORDS[6]} ${RED}${WORDS[7]} ${GREEN}${WORDS[8]}${NC}"
