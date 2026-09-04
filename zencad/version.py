import OCP

# Keep the runtime version independent of possibly stale editable-install
# metadata.  Wheel smoke tests ensure this value matches pyproject.toml.
__version__ = "2.0.0"

__ocp_version__ = OCP.__version__
