package main

import (
	"casekit/internal/cli"
	"os"
)

var version = "dev"

func main() { os.Exit(cli.Run(os.Args[1:], os.Stdout, os.Stderr, version)) }
