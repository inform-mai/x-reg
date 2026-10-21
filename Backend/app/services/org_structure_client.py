from Backend.app.api.schemas import OrgSnapshotResponse


class OrgStructureClientError(RuntimeError):
    pass

class OrgStructureClient:
  

    def fetch_snapshot(self) -> OrgSnapshotResponse:
        pass
