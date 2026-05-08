use assert_cmd::Command;

#[test]
fn check_command_succeeds() {
    let mut command = Command::cargo_bin("{{ package_name }}").expect("generated CLI binary");

    command
        .arg("check")
        .assert()
        .success()
        .stdout("ok: local\n");
}

#[test]
fn help_command_succeeds() {
    let output = Command::cargo_bin("{{ package_name }}")
        .expect("generated CLI binary")
        .arg("--help")
        .output()
        .expect("run help command");

    assert!(output.status.success());
    assert!(String::from_utf8_lossy(&output.stdout).contains("Usage:"));
}

#[test]
fn version_command_succeeds() {
    let output = Command::cargo_bin("{{ package_name }}")
        .expect("generated CLI binary")
        .arg("--version")
        .output()
        .expect("run version command");

    assert!(output.status.success());
    assert!(String::from_utf8_lossy(&output.stdout).contains(env!("CARGO_PKG_VERSION")));
}
