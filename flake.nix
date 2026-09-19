{
  description = "Golem: use Large Language Model APIs from the command line";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python3 = pkgs.python3;

        pythonEnv = python3.withPackages (ps: with ps; [
          pandas
          pyyaml
          requests
          pylint
        ]);
      in
      {
        packages.default = python3.pkgs.buildPythonApplication {
          pname = "golem";
          version = "0.1";
          pyproject = true;

          src = ./.;

          build-system = [ python3.pkgs.setuptools ];

          dependencies = with python3.pkgs; [
            pandas
            pyyaml
            requests
          ];

          # The Makefile's tests all make live, paid API calls to
          # external providers and need credentials, so there's
          # nothing safe to run in a sandboxed build.
          doCheck = false;

          meta = {
            description = "Use Large Language Model APIs from the command line";
            homepage = "https://github.com/RobBlackwell/golem";
            license = pkgs.lib.licenses.gpl3Only;
            mainProgram = "golem";
          };
        };

        checks.pylint = pkgs.runCommand "golem-pylint"
          {
            buildInputs = [ pythonEnv ];
          } ''
            export HOME="$TMPDIR"
            cp -r ${self} golem
            cd golem
            pylint -d duplicate-code $(find . -name '*.py' -not -path './.git/*')
            touch $out
          '';

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.jq
            pkgs.uv
          ];

          shellHook = ''
            echo "golem dev shell: python=$(python3 --version), jq=$(jq --version)"
            echo "Run './golem.py --provider ollama \"Why is the sky blue?\"' to try it out."
          '';
        };
      });
}
