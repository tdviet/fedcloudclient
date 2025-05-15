# shellcheck disable=SC2148,SC2034,SC2206,SC2162,SC2086
# Script for shell completion for fedcloud
# Add it to .bashrc for enabling shell completion

_fedcloud_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD _FEDCLOUD_COMPLETE=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

_fedcloud_completion_setup() {
    complete -o nosort -F _fedcloud_completion fedcloud
}

_fedcloud_completion_setup;

