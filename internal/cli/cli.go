// Package cli shares Phase 0 argument handling between the two entry points.
package cli

import (
	"flag"
	"fmt"
	"io"

	"casekit/internal/config"
)

func Run(args []string, stdout, stderr io.Writer, version string) int {
	flags := flag.NewFlagSet("casekit", flag.ContinueOnError)
	flags.SetOutput(stderr)
	showVersion := flags.Bool("version", false, "print build version")
	configPath := flags.String("config", "", "read a TOML configuration file")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() != 0 {
		fmt.Fprintln(stderr, "casekit: unexpected arguments; extraction is not implemented in Phase 0")
		return 2
	}
	if *showVersion {
		if _, err := fmt.Fprintln(stdout, version); err != nil {
			return 1
		}
		return 0
	}
	if _, err := config.Load(*configPath); err != nil {
		fmt.Fprintln(stderr, "casekit:", err)
		return 1
	}
	flags.PrintDefaults()
	return 0
}
