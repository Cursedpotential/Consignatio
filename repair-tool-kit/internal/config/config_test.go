package config

import (
	"errors"
	"io/fs"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadDefaults(t *testing.T) {
	root, err := moduleRoot()
	if err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{"", filepath.Join("testdata", "defaults.toml")} {
		cfg, err := Load(path)
		if err != nil {
			t.Fatalf("Load(%q): %v", path, err)
		}
		if cfg.InstallRoot != filepath.Join(root, DefaultInstallRoot) {
			t.Errorf("Load(%q).InstallRoot = %q; want %q", path, cfg.InstallRoot, DefaultInstallRoot)
		}
	}
}

func TestLoadOverride(t *testing.T) {
	cfg, err := Load(filepath.Join("testdata", "override.toml"))
	if err != nil {
		t.Fatal(err)
	}
	root, err := moduleRoot()
	if err != nil {
		t.Fatal(err)
	}
	if cfg.InstallRoot != filepath.Join(root, "runtime-codex", "custom root é") {
		t.Errorf("unexpected root: %q", cfg.InstallRoot)
	}
}

func TestRejectOutsideProject(t *testing.T) {
	for _, path := range []string{"../outside-codex", "..", "."} {
		if _, err := withinProject(Config{InstallRoot: path}); err == nil {
			t.Errorf("accepted outside/non-subdirectory root %q", path)
		}
	}
}

func TestLoadRejectsInvalidFiles(t *testing.T) {
	for _, tc := range []struct{ file, message string }{
		{"malformed.toml", "load config"},
		{"wrong_type.toml", "load config"},
		{"unknown.toml", "unknown fields"},
		{"empty.toml", "install_root cannot be empty"},
		{"whitespace.toml", "install_root cannot be empty"},
	} {
		t.Run(tc.file, func(t *testing.T) {
			cfg, err := Load(filepath.Join("testdata", tc.file))
			if err == nil || !strings.Contains(err.Error(), tc.message) {
				t.Fatalf("error = %v; want message containing %q", err, tc.message)
			}
			if cfg != (Config{}) {
				t.Errorf("error returned partially usable config: %+v", cfg)
			}
		})
	}
}

func TestLoadExplicitMissingFile(t *testing.T) {
	_, err := Load(filepath.Join("testdata", "does-not-exist.toml"))
	if !errors.Is(err, fs.ErrNotExist) {
		t.Fatalf("error = %v; want wrapped missing-file error", err)
	}
}
