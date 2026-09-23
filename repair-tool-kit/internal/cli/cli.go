// Updated by: Codex (case-bible/mp-handoff-protocol) | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: Add frozen-fixture engine certification | Context: Platform identity and extraction behavior must be recorded together before an engine is trusted
// Package cli shares argument handling between the two entry points.
package cli

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"path/filepath"
	"strings"
	"text/tabwriter"
	"time"

	"casekit/internal/config"
	"casekit/internal/engine"
)

func Run(args []string, stdout, stderr io.Writer, version string) int {
	if len(args) > 0 && args[0] == "doctor" {
		return runDoctor(args[1:], stdout, stderr)
	}
	if len(args) > 0 && args[0] == "certify-engine" {
		return runCertifyEngine(args[1:], stdout, stderr)
	}
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

func runCertifyEngine(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("casekit certify-engine", flag.ContinueOnError)
	flags.SetOutput(stderr)
	configPath := flags.String("config", "", "read a TOML configuration file")
	profileID := flags.String("profile", "", "engine profile ID to certify")
	fixturePath := flags.String("fixture", "", "exact 33-glyph reference PDF")
	outputDir := flags.String("output-dir", "", "new certification directory under install_root")
	timeout := flags.Duration("timeout", 30*time.Second, "maximum total identity and extraction time")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() != 0 || strings.TrimSpace(*profileID) == "" || strings.TrimSpace(*fixturePath) == "" {
		fmt.Fprintln(stderr, "casekit certify-engine: --profile and --fixture are required; positional arguments are not accepted")
		return 2
	}
	if *timeout <= 0 {
		fmt.Fprintln(stderr, "casekit certify-engine: timeout must be greater than zero")
		return 2
	}
	cfg, err := config.Load(*configPath)
	if err != nil {
		fmt.Fprintln(stderr, "casekit certify-engine:", err)
		return 1
	}
	projectRoot, err := config.ProjectDirectory()
	if err != nil {
		fmt.Fprintln(stderr, "casekit certify-engine:", err)
		return 1
	}
	profiles, err := engine.Discover(filepath.Join(projectRoot, "engines"))
	if err != nil {
		fmt.Fprintln(stderr, "casekit certify-engine:", err)
		return 1
	}
	var selected *engine.Profile
	for index := range profiles {
		if profiles[index].Manifest.ProfileID == *profileID {
			selected = &profiles[index]
			break
		}
	}
	if selected == nil {
		fmt.Fprintf(stderr, "casekit certify-engine: unknown profile %q\n", *profileID)
		return 1
	}
	destination := *outputDir
	if destination == "" {
		destination = filepath.Join(cfg.InstallRoot, "certifications", *profileID, time.Now().UTC().Format("20060102T150405.000000000Z"))
	}
	ctx, cancel := context.WithTimeout(context.Background(), *timeout)
	defer cancel()
	record, certifyErr := engine.CertifyPDFText(ctx, *selected, cfg.InstallRoot, *fixturePath, destination, engine.ReferencePDFSpec)
	encoder := json.NewEncoder(stdout)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(record); err != nil {
		fmt.Fprintln(stderr, "casekit certify-engine: encode report:", err)
		return 1
	}
	if certifyErr != nil {
		fmt.Fprintln(stderr, "casekit certify-engine:", certifyErr)
		return 1
	}
	return 0
}

func runDoctor(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("casekit doctor", flag.ContinueOnError)
	flags.SetOutput(stderr)
	configPath := flags.String("config", "", "read a TOML configuration file")
	jsonOutput := flags.Bool("json", false, "emit complete JSON probe records")
	timeout := flags.Duration("timeout", 10*time.Second, "maximum time for each identity probe")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() != 0 {
		fmt.Fprintln(stderr, "casekit doctor: unexpected arguments")
		return 2
	}
	if *timeout <= 0 {
		fmt.Fprintln(stderr, "casekit doctor: timeout must be greater than zero")
		return 2
	}
	cfg, err := config.Load(*configPath)
	if err != nil {
		fmt.Fprintln(stderr, "casekit doctor:", err)
		return 1
	}
	projectRoot, err := config.ProjectDirectory()
	if err != nil {
		fmt.Fprintln(stderr, "casekit doctor:", err)
		return 1
	}
	profiles, err := engine.Discover(filepath.Join(projectRoot, "engines"))
	if err != nil {
		fmt.Fprintln(stderr, "casekit doctor:", err)
		return 1
	}
	records := engine.Doctor(context.Background(), profiles, cfg.InstallRoot, *timeout)
	if *jsonOutput {
		encoder := json.NewEncoder(stdout)
		encoder.SetIndent("", "  ")
		if err := encoder.Encode(records); err != nil {
			fmt.Fprintln(stderr, "casekit doctor: encode report:", err)
			return 1
		}
	} else if err := writeDoctorTable(stdout, records); err != nil {
		fmt.Fprintln(stderr, "casekit doctor: write report:", err)
		return 1
	}
	for _, record := range records {
		if record.ProbeStatus == engine.ProbeFailed {
			return 1
		}
	}
	return 0
}

func writeDoctorTable(output io.Writer, records []engine.ProbeRecord) error {
	table := tabwriter.NewWriter(output, 0, 4, 2, ' ', 0)
	if _, err := fmt.Fprintln(table, "PROFILE\tTARGET\tVERSION\tEXECUTABLE SHA-256\tRESOLVED PATH\tCAPABILITIES\tCOMMAND\tCHECKS\tPROBE\tCERTIFICATION"); err != nil {
		return err
	}
	for _, record := range records {
		command := "-"
		if record.Invocation != nil {
			command = record.Invocation.Display
		}
		checks := make([]string, 0, len(record.ExtractionChecks))
		for _, check := range record.ExtractionChecks {
			checks = append(checks, check.ID+"="+check.Status)
		}
		if _, err := fmt.Fprintf(table, "%s\t%s/%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n",
			record.EngineProfileID, record.DeclaredOS, record.DeclaredArchitecture,
			valueOrDash(record.EngineVersion), valueOrDash(record.ExecutableSHA256), valueOrDash(record.ResolvedPath),
			strings.Join(record.Capabilities, ","), command, strings.Join(checks, ","),
			record.ProbeStatus, record.CertificationStatus); err != nil {
			return err
		}
		if record.Error != "" {
			if _, err := fmt.Fprintf(table, "\t\t\t\t\t\t\t\tERROR: %s\t\n", record.Error); err != nil {
				return err
			}
		}
	}
	return table.Flush()
}

func valueOrDash(value string) string {
	if value == "" {
		return "-"
	}
	return value
}
