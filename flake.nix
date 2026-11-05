{
  description = "Email autoconfig library";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        mylDiscovery = pkgs.python3Packages.buildPythonApplication {
          pname = "myl-discovery";
          version = builtins.readFile ./myl-discovery-version.txt;
          pyproject = true;

          src = ./.;

          pythonRelaxDeps = [ "rich" ];

          buildInputs = [
            pkgs.python3Packages.setuptools
            pkgs.python3Packages.setuptools-scm
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            dnspython
            exchangelib
            requests
            rich
            xmltodict
          ];

          pythonImportsCheck = [ "myldiscovery" ];

          meta = {
            description = "Email autodiscovery";
            homepage = "https://github.com/pschmitt/myl-discovery";
            license = pkgs.lib.licenses.gpl3Only;
            maintainers = with pkgs.lib.maintainers; [ pschmitt ];
            platforms = pkgs.lib.platforms.all;
          };
        };

        devShell = pkgs.mkShell {
          name = "myl-discovery-devshell";

          inputsFrom = [ mylDiscovery ];

          nativeBuildInputs = [
            pkgs.gh # GitHub CLI
            pkgs.git
            pkgs.python3Packages.ipython
            pkgs.neovim
          ];

          shellHook = ''
            export PYTHONPATH="$PWD''${PYTHONPATH:+:$PYTHONPATH}"
            echo -e "\e[34mWelcome to the myl-discovery development shell!\e[0m"
          '';
        };
      in
      {
        packages = {
          "myl-discovery" = mylDiscovery;
          default = mylDiscovery;
        };

        devShells.default = devShell;
      }
    );
}
