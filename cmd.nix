with import <nixpkgs> {
  overlays = [
    (self: super: rec {
      smartbox = super.nur.repos.graham33.smartbox.overrideAttrs (o : {
        src = ./.;
      });
    })
  ];
};
mkShell {
  buildInputs = [
    smartbox
  ];
}
