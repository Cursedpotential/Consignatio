package main

import (
	"casekit/internal/cli"
	"io"
	"os"
)

var version = "dev"

func main() {
	// Explorer provides no stdout handle. Preserve output when a caller supplies
	// a pipe or file, but do not fail a windowless launch for lacking a console.
	var output io.Writer = os.Stdout
	if _, err := os.Stdout.Stat(); err != nil {
		output = io.Discard
	}
	os.Exit(cli.Run(os.Args[1:], output, os.Stderr, version))
}
