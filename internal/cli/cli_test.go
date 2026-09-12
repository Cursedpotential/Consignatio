package cli

import (
	"bytes"
	"testing"
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
