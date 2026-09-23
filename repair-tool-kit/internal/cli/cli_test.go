// Updated by: Codex (case-bible/mp-handoff-protocol) | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: Validate certification command argument boundaries | Context: Fixture certification must be explicit and never scan positional paths
package cli

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"casekit/internal/config"
	"casekit/internal/engine"
)

func TestArguments(t *testing.T) {
	for _, tc := range []struct {
		name   string
		args   []string
		code   int
		output string
	}{
		{"version", []string{"--version"}, 0, "phase0-test\n"},
		{"version does not load config", []string{"--config", "missing.toml", "--version"}, 0, "phase0-test\n"},
		{"unknown flag", []string{"--unknown"}, 2, ""},
		{"unexpected input", []string{"source.pdf"}, 2, ""},
		{"missing config", []string{"--config", "missing.toml"}, 1, ""},
		{"help", []string{"--help"}, 0, ""},
		{"no args", nil, 0, ""},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var out, diagnostic bytes.Buffer
			if code := Run(tc.args, &out, &diagnostic, "phase0-test"); code != tc.code {
				t.Fatalf("code = %d, want %d: %s", code, tc.code, diagnostic.String())
			}
			if out.String() != tc.output {
				t.Fatalf("stdout = %q, want %q", out.String(), tc.output)
			}
			if tc.code != 0 && diagnostic.Len() == 0 {
				t.Fatal("missing error diagnostic")
			}
		})
	}
}

func TestCLIEngineHelperProcess(t *testing.T) {
	if os.Getenv("CASEKIT_CLI_ENGINE_HELPER") != "1" {
		return
	}
	fmt.Fprintln(os.Stdout, "cli-fake 2.0.0")
	os.Exit(0)
}

func TestDoctorJSONReportsCurrentAndForeignProfiles(t *testing.T) {
	projectRoot := filepath.Join(t.TempDir(), "project root é")
	previousRoot := config.ProjectRoot
	config.ProjectRoot = projectRoot
	t.Cleanup(func() { config.ProjectRoot = previousRoot })

	installRoot := filepath.Join(projectRoot, config.DefaultInstallRoot)
	runtimeRelative := filepath.Join("engines", "fake current", cliExecutableName("fake"))
	runtimePath := filepath.Join(installRoot, runtimeRelative)
	if err := os.MkdirAll(filepath.Dir(runtimePath), 0o755); err != nil {
		t.Fatal(err)
	}
	copyCLIExecutable(t, runtimePath)
	writeCLIManifest(t, projectRoot, "fake-current", fmt.Sprintf(`
profile_id = "fake-%s-%s"
engine_id = "fake"
lang = "go-test"
os = "%s"
architecture = "%s"
runtime = %q
mode = "oneshot"
capabilities = ["extract_text"]
formats = ["pdf"]
version_cmd = ["-test.run=TestCLIEngineHelperProcess"]
extraction_checks = ["symbol_glyph_count"]
`, runtime.GOOS, runtime.GOARCH, runtime.GOOS, runtime.GOARCH, filepath.ToSlash(runtimeRelative)))

	foreignOS := "linux"
	if runtime.GOOS == foreignOS {
		foreignOS = "windows"
	}
	writeCLIManifest(t, projectRoot, "fake-foreign", fmt.Sprintf(`
profile_id = "foreign-%s-%s"
engine_id = "foreign"
lang = "test"
os = "%s"
architecture = "%s"
runtime = "engines/foreign/missing"
mode = "oneshot"
capabilities = ["extract_text"]
formats = ["pdf"]
version_cmd = ["--version"]
extraction_checks = ["symbol_glyph_count"]
`, foreignOS, runtime.GOARCH, foreignOS, runtime.GOARCH))

	t.Setenv("CASEKIT_CLI_ENGINE_HELPER", "1")
	var out, diagnostic bytes.Buffer
	if code := Run([]string{"doctor", "--json", "--timeout", "3s"}, &out, &diagnostic, "test"); code != 0 {
		t.Fatalf("doctor code = %d: %s", code, diagnostic.String())
	}
	var records []engine.ProbeRecord
	if err := json.Unmarshal(out.Bytes(), &records); err != nil {
		t.Fatalf("decode doctor JSON: %v\n%s", err, out.String())
	}
	if len(records) != 2 {
		t.Fatalf("record count = %d, want 2", len(records))
	}
	statuses := make(map[string]string)
	for _, record := range records {
		statuses[record.EngineID] = record.ProbeStatus
		if record.CertificationStatus != "pending" || len(record.ExtractionChecks) != 1 {
			t.Errorf("missing pending extraction status: %+v", record)
		}
	}
	if statuses["fake"] != engine.ProbeIdentityOK || statuses["foreign"] != engine.ProbeNotTarget {
		t.Fatalf("unexpected statuses: %+v", statuses)
	}
	if strings.Contains(diagnostic.String(), "missing") {
		t.Fatalf("foreign runtime was resolved or executed: %s", diagnostic.String())
	}
}

func TestCertifyEngineRequiresExplicitProfileAndFixture(t *testing.T) {
	for _, args := range [][]string{
		{"certify-engine"},
		{"certify-engine", "--profile", "poppler-windows-amd64"},
		{"certify-engine", "--fixture", "fixture.pdf"},
		{"certify-engine", "--profile", "x", "--fixture", "y", "extra"},
	} {
		var out, diagnostic bytes.Buffer
		if code := Run(args, &out, &diagnostic, "test"); code != 2 {
			t.Fatalf("Run(%q) code = %d, want 2", args, code)
		}
		if diagnostic.Len() == 0 || out.Len() != 0 {
			t.Fatalf("Run(%q) output=%q diagnostic=%q", args, out.String(), diagnostic.String())
		}
	}
}

func writeCLIManifest(t *testing.T, projectRoot, directory, body string) {
	t.Helper()
	path := filepath.Join(projectRoot, "engines", directory, "engine.toml")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(strings.TrimSpace(body)+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
}

func copyCLIExecutable(t *testing.T, destination string) {
	t.Helper()
	source, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	in, err := os.Open(source)
	if err != nil {
		t.Fatal(err)
	}
	defer in.Close()
	out, err := os.OpenFile(destination, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o755)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		t.Fatal(err)
	}
	if err := out.Close(); err != nil {
		t.Fatal(err)
	}
}

func cliExecutableName(base string) string {
	if runtime.GOOS == "windows" {
		return base + ".exe"
	}
	return base
}
