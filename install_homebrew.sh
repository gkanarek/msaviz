#!/bin/bash
set -ue
NEW_BREW_PREFIX="local"

if [[ $(which ruby) != "/usr/bin/ruby" ]]
then
    echo "Ruby wasn't found in the default location. Perhaps you've customized things?"
    exit 1
fi

cd
destination="$HOME/$NEW_BREW_PREFIX/homebrew"
if [ -d $destination ];
then
    echo "There's already something in $destination"
    echo "Remove $HOME/$NEW_BREW_PREFIX to get a fresh start"
    exit 1
fi

echo "Copying the Homebrew package manager into $destination"
git clone https://github.com/Homebrew/homebrew.git $destination

mkdir -p "$HOME/$NEW_BREW_PREFIX/bin" \
    "$HOME/$NEW_BREW_PREFIX/share/man/man1" \
    "$HOME/$NEW_BREW_PREFIX/etc"

ln -s "$HOME/$NEW_BREW_PREFIX/homebrew/bin/brew" \
    "$HOME/$NEW_BREW_PREFIX/bin/brew"

ln -s "$HOME/$NEW_BREW_PREFIX/homebrew/share/man/man1/brew.1" \
    "$HOME/$NEW_BREW_PREFIX/share/man/man1/brew.1"

export PATH="$HOME/$NEW_BREW_PREFIX/bin:$PATH"

brew update

echo "
export _old_PATH=\"\$PATH\"
export PATH=\"\$HOME/$NEW_BREW_PREFIX/bin:\$PATH\"
export _old_MANPATH=\"\$MANPATH\"
export MANPATH=\"\$HOME/$NEW_BREW_PREFIX/share/man:\$MANPATH\"" > "$HOME/$NEW_BREW_PREFIX/bin/brew_activate.sh"

echo "
export PATH=\"\$_old_PATH\"
unset _old_PATH
export MANPATH=\"\$_old_MANPATH\"
unset _old_MANPATH" > "$HOME/$NEW_BREW_PREFIX/bin/brew_deactivate.sh"

echo
echo "***** Install complete *****"
echo
echo "It is recommended to add the following aliases to your ~/.bash_profile:

alias brew_activate=\"source $HOME/$NEW_BREW_PREFIX/bin/brew_activate.sh\"
alias brew_deactivate=\"source $HOME/$NEW_BREW_PREFIX/bin/brew_deactivate.sh\"

Then, open a new shell. Type \"brew_activate\" to add Homebrew to the path, along with everything installed through it."