// Package config loads the Phase 0 installation configuration without modifying disk.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/BurntSushi/toml"
)

const DefaultInstallRoot = "runtime-codex"

// ProjectRoot is injected by the Windows build script. Development/test runs
// discover the module root; no drive-root installation fallback exists.
var ProjectRoot string

func moduleRoot() (string, error) {
	if ProjectRoot != "" {
		return filepath.Abs(ProjectRoot)
	}
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}
	for {
		data, err := os.ReadFile(filepath.Join(dir, "go.mod"))
		if err == nil && strings.HasPrefix(string(data), "module casekit\n") {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("casekit module root not found; run from the project directory")
		}
		dir = parent
	}
}

func withinProject(cfg Config) (Config, error) {
	root, err := moduleRoot()
	if err != nil {
		return Config{}, err
	}
	path := cfg.InstallRoot
	if !filepath.IsAbs(path) {
		path = filepath.Join(root, path)
	}
	path = filepath.Clean(path)
	rel, err := filepath.Rel(root, path)
	if err != nil || rel == "." || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return Config{}, fmt.Errorf("install_root must be a subdirectory of the casekit project")
	}
	// Check existing ancestors so a junction cannot redirect a future caller.
	for check := path; check != root; check = filepath.Dir(check) {
		if _, err := os.Lstat(check); err == nil {
			real, err := filepath.EvalSymlinks(check)
			if err != nil {
				return Config{}, err
			}
			r, err := filepath.Rel(root, real)
			if err != nil || r == ".." || strings.HasPrefix(r, ".."+string(filepath.Separator)) {
				return Config{}, fmt.Errorf("install_root resolves outside the project")
			}
		} else if !os.IsNotExist(err) {
			return Config{}, err
		}
	}
	cfg.InstallRoot = path
	return cfg, nil
}

type Config struct {
	InstallRoot string `toml:"install_root"`
}

// Load returns defaults when path is empty. An explicitly supplied file must
// exist and contain valid TOML with no unknown fields. Omitted fields retain
// their defaults; an explicitly empty installation root is rejected.
// Loading configuration never creates the installation directory.
func Load(path string) (Config, error) {
	cfg := Config{InstallRoot: DefaultInstallRoot}
	if path == "" {
		return withinProject(cfg)
	}
	metadata, err := toml.DecodeFile(path, &cfg)
	if err != nil {
		return Config{}, fmt.Errorf("load config %q: %w", path, err)
	}
	if unknown := metadata.Undecoded(); len(unknown) != 0 {
		return Config{}, fmt.Errorf("load config %q: unknown fields %v", path, unknown)
	}
	if strings.TrimSpace(cfg.InstallRoot) == "" {
		return Config{}, fmt.Errorf("load config %q: install_root cannot be empty", path)
	}
	return withinProject(cfg)
}
