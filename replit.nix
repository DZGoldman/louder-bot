{pkgs}: {
  deps = [
    pkgs.chromedriver
    pkgs.geckodriver
    pkgs.xvfb-run
    pkgs.at-spi2-core
    pkgs.firefox
    pkgs.mesa
    pkgs.gtk3
    pkgs.alsa-lib
    pkgs.dbus
    pkgs.chromium
    pkgs.playwright-driver
    pkgs.gitFull
  ];
}
