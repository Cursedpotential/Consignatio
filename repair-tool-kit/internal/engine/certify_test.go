// Updated by: Codex (case-bible/mp-handoff-protocol) | Date: 2026-09-12 | Rev: 2 | Platform: Codex / win32 | Changes: Correct fake Poppler extraction argv length | Context: The real command has six arguments after the test helper separator
package engine

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestCertificationHelperProcess(t *testing.T) {
	if os.Getenv("CASEKIT_CERTIFICATION_HELPER") != "1" {
		return
	}
	separator := -1
	for index, value := range os.Args {
		if value == "--" {
			separator = index
			break
		}
	}
	if separator < 0 || separator+1 >= len(os.Args) {
		os.Exit(91)
	}
	args := os.Args[separator+1:]
	if args[0] == "version" {
		fmt.Fprintln(os.Stdout, "fixture-helper 1.0.0")
		os.Exit(0)
	}
	if len(args) != 6 || args[0] != "-enc" || args[1] != "UTF-8" || args[2] != "-eol" || args[3] != "unix" {
		os.Exit(92)
	}
	if err := os.WriteFile(args[5], []byte("hello \u25a0\u25a0\u25a0\n"), 0o600); err != nil {
		os.Exit(93)
	}
	os.Exit(0)
}

func TestCertifyPDFTextPersistsPassingRecord(t *testing.T) {
	manifestRoot := filepath.Join(t.TempDir(), "manifests")
	installRoot := filepath.Join(t.TempDir(), "runtime é")
	runtimeRelative := filepath.Join("engines", "poppler helper", executableName("poppler-helper"))
	runtimePath := filepath.Join(installRoot, runtimeRelative)
	if err := os.MkdirAll(filepath.Dir(runtimePath), 0o755); err != nil {
		t.Fatal(err)
	}
	copyExecutable(t, runtimePath)
	writeManifest(t, manifestRoot, "poppler", fmt.Sprintf(`
profile_id = "poppler-%s-%s"
engine_id = "poppler"
lang = "go-test"
os = "%s"
architecture = "%s"
runtime = %q
entry = ["-test.run=TestCertificationHelperProcess", "--"]
mode = "oneshot"
capabilities = ["extract_text"]
formats = ["pdf"]
version_cmd = ["version"]
extraction_checks = ["symbol_glyph_count", "symbol_glyph_codepoint", "replacement_chars", "char_volume"]
`, runtime.GOOS, runtime.GOARCH, runtime.GOOS, runtime.GOARCH, filepath.ToSlash(runtimeRelative)))
	profiles, err := Discover(manifestRoot)
	if err != nil {
		t.Fatal(err)
	}

	fixturePath := filepath.Join(t.TempDir(), "fixture space é.pdf")
	fixtureData := []byte("small immutable fixture")
	if err := os.WriteFile(fixturePath, fixtureData, 0o400); err != nil {
		t.Fatal(err)
	}
	fixtureHash := sha256.Sum256(fixtureData)
	spec := FixtureSpec{
		ID: "test-fixture", Bytes: int64(len(fixtureData)), SHA256: hex.EncodeToString(fixtureHash[:]),
		ExpectedGlyph: '\u25a0', ExpectedGlyphCount: 3, MaximumReplacementCharacters: 0,
		MinimumCharacters: 9, MaximumCharacters: 10,
	}
	outputDir := filepath.Join(installRoot, "certifications", "run space é")
	t.Setenv("CASEKIT_CERTIFICATION_HELPER", "1")
	record, err := CertifyPDFText(context.Background(), profiles[0], installRoot, fixturePath, outputDir, spec)
	if err != nil {
		t.Fatalf("certification failed: %v\n%+v", err, record)
	}
	if record.Status != "passed" || record.Profile.CertificationStatus != "passed" {
		t.Fatalf("unexpected record status: %+v", record)
	}
	if record.Output == nil || record.Output.UnicodeCharacters != 10 {
		t.Fatalf("unexpected output record: %+v", record.Output)
	}
	if !strings.Contains(strings.Join(record.Invocation.Argv, " "), "fixture space é.pdf") {
		t.Fatalf("opaque fixture path was not preserved: %+v", record.Invocation.Argv)
	}
	if _, err := os.Stat(filepath.Join(outputDir, "certification.json")); err != nil {
		t.Fatalf("missing certification record: %v", err)
	}
}

func TestCertifyRejectsWrongFixtureBeforeCreatingOutput(t *testing.T) {
	fixturePath := filepath.Join(t.TempDir(), "wrong.pdf")
	if err := os.WriteFile(fixturePath, []byte("wrong"), 0o400); err != nil {
		t.Fatal(err)
	}
	outputDir := filepath.Join(t.TempDir(), "runtime", "certifications", "must-not-exist")
	_, err := CertifyPDFText(context.Background(), Profile{}, filepath.Dir(filepath.Dir(outputDir)), fixturePath, outputDir, FixtureSpec{Bytes: 5, SHA256: strings.Repeat("0", 64)})
	if err == nil || !strings.Contains(err.Error(), "SHA-256 mismatch") {
		t.Fatalf("error = %v", err)
	}
	if _, statErr := os.Stat(outputDir); !os.IsNotExist(statErr) {
		t.Fatalf("output directory created before fixture validation: %v", statErr)
	}
}
