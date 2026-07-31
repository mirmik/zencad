import sys
import unittest
from unittest.mock import patch

import zencad


class ImportProbe(unittest.TestCase):
    def test_legacy_assembly_is_lazy_and_diagnostic(self):
        self.assertNotIn("zencad.assemble", sys.modules)

        with patch.object(
            zencad.importlib,
            "import_module",
            side_effect=ModuleNotFoundError("termin.geombase"),
        ):
            with self.assertRaisesRegex(
                ImportError,
                "requires a compatible legacy Termin kinematic API",
            ):
                zencad.assemble


if __name__ == "__main__":
    unittest.main()
