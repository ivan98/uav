{
  description = "Dev environment for uav-downloader";

  inputs = {
    # Resolves through the flake registry, which on NixOS points at the
    # system's own nixpkgs — so the dev shells reuse the system's Python and
    # libraries from /nix/store instead of downloading a second copy. The lock
    # file pins that store path; after a `nixos-rebuild`, run
    # `nix flake update nixpkgs` to follow the new system nixpkgs.
    nixpkgs.url = "nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # nixpkgs' default Python — whatever the system's nixpkgs ships, rather
        # than a pinned minor version that would be a separate download.
        python = pkgs.python3;

        # Lets pip-installed binary wheels (numpy, ctranslate2, pycryptodome,
        # curl_cffi, ...) dlopen libstdc++/libgomp/zlib at runtime — NixOS has
        # no FHS paths (/usr/lib etc.) for them to fall back to. If a package
        # still fails with "cannot open shared object file", add the missing
        # lib here.
        runtimeLibs = with pkgs; [
          stdenv.cc.cc.lib
          zlib
        ];

        # nixpkgs' base python312 omits the _tkinter C extension (Tcl/Tk is an
        # optional build input); it ships as this separate package instead.
        # Exposing it via PYTHONPATH lets stdlib `tkinter` (already present in
        # every venv) find it, without needing a python.withPackages wrapper
        # (which `venv --system-site-packages` can't see through anyway).
        tkinterPythonPath = "${python.pkgs.tkinter}/${python.sitePackages}";

        mkPipShell = { venvDir, requirementsFile, extraPackages ? [ ], extraPythonPath ? null }:
          pkgs.mkShell {
            packages = [ python pkgs.ffmpeg ] ++ extraPackages;

            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath runtimeLibs;
            IMAGEIO_FFMPEG_EXE = "${pkgs.ffmpeg}/bin/ffmpeg";
            PYTHONPATH = extraPythonPath;

            shellHook = ''
              venv_dir="${venvDir}"
              req_file="${requirementsFile}"
              stamp="$venv_dir/.req-stamp"

              # Recreate the venv if the system Python moved to another
              # minor version (venv/bin/python would dangle or be stale).
              if [ -d "$venv_dir" ] && \
                 [ "$("$venv_dir/bin/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" != "${python.pythonVersion}" ]; then
                echo "uav-downloader: Python changed, recreating $venv_dir"
                rm -rf "$venv_dir"
              fi

              if [ ! -d "$venv_dir" ]; then
                echo "uav-downloader: creating virtualenv in $venv_dir"
                ${python.interpreter} -m venv "$venv_dir"
              fi

              # shellcheck disable=SC1091
              source "$venv_dir/bin/activate"

              req_hash="$(sha256sum "$req_file" | cut -d' ' -f1)"
              if [ ! -f "$stamp" ] || [ "$(cat "$stamp")" != "$req_hash" ]; then
                echo "uav-downloader: installing deps from $req_file"
                pip install --quiet --disable-pip-version-check -r "$req_file" \
                  && echo "$req_hash" > "$stamp"
              fi

              # Editable install of the project itself (deps come from the
              # requirements file above) so the console scripts — uav,
              # uav-browser, uav-watcher, ... — land on PATH. Re-runs when
              # pyproject.toml changes (entry points live there).
              pkg_stamp="$venv_dir/.pkg-stamp"
              pkg_hash="$(sha256sum pyproject.toml | cut -d' ' -f1)"
              if [ ! -f "$pkg_stamp" ] || [ "$(cat "$pkg_stamp")" != "$pkg_hash" ]; then
                echo "uav-downloader: installing project (editable)"
                pip install --quiet --disable-pip-version-check --no-deps -e . \
                  && echo "$pkg_hash" > "$pkg_stamp"
              fi
            '';
          };
      in
      {
        devShells.default = mkPipShell {
          venvDir = ".venv";
          requirementsFile = "requirements-docker.txt";
        };

        devShells.gui = mkPipShell {
          venvDir = ".venv-gui";
          requirementsFile = "requirements.txt";
          extraPackages = with pkgs; [ tcl tk ];
          extraPythonPath = tkinterPythonPath;
        };
      });
}
