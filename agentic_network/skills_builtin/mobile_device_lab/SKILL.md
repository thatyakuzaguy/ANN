# Mobile Device Lab

Android, iOS, Flutter, and React Native device-lab readiness and external evidence verification.

## Actions

- inspect: Inspect Android, iOS, Flutter, and React Native device-test readiness.
- verify: Verify supplied device-lab evidence without starting host emulators or executing project binaries.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
