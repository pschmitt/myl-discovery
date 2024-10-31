{
  description = "Email autoconfig library";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
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
          version = builtins.readFile ./version.txt;
          pyproject = true;

          src = ./.;

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

          buildInputs = [
            pkgs.python3
            pkgs.python3Packages.dnspython
            pkgs.python3Packages.exchangelib
            pkgs.python3Packages.requests
            pkgs.python3Packages.rich
            pkgs.python3Packages.setuptools
            pkgs.python3Packages.setuptools-scm
            pkgs.python3Packages.xmltodict
          ];

          # Additional development tools
          nativeBuildInputs = [
            pkgs.gh # GitHub CLI
            pkgs.git
            pkgs.python3Packages.ipython
            pkgs.neovim
          ];

          # Environment variables and shell hooks
          shellHook = ''
            export PYTHONPATH=${self.packages.${system}.default}/lib/python3.x/site-packages
            echo -e "\e[34mWelcome to the myl-discovery development shell!\e[0m"
            # Activate a virtual environment if desired
            # source .venv/bin/activate
          '';

          # Optional: Set up a Python virtual environment
          # if you prefer using virtualenv or similar tools
          # you can uncomment and configure the following lines
          # shellHook = ''
          #   if [ ! -d .venv ]; then
          #     python3 -m venv .venv
          #     source .venv/bin/activate
          #     pip install --upgrade pip
          #   else
          #     source .venv/bin/activate
          #   fi
          # '';
        };
      in
      {
        # pkgs
        packages."myl-discovery" = mylDiscovery;
        defaultPackage = mylDiscovery;

        devShells.default = devShell;
      }
    );
}
