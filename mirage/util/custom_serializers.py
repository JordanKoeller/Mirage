from .dictify import Dictify, CustomSerializer

from astropy.units import Quantity
from astropy import cosmology as cosmo


def register_serializers():
  from mirage.model import initial_mass_function
  # Custom Serializer for Quantity
  Dictify.register_serializer(
      CustomSerializer(
          value_type=Quantity,
          to_dict=lambda q: f"{int(q.value) if q.value.is_integer() else float(q.value)} {q.unit.to_string()}",
          from_dict=lambda value_str: Quantity(
              *(float(value_str.split(" ")[0].strip()), "".join(value_str.split(" ")[1:]).strip())
              if isinstance(value_str, str)
              else value_str
          ),
      )
  )

  # Custom Serializer for Cosmology objects
  Dictify.register_serializer(
      CustomSerializer(
          value_type=cosmo.Cosmology,
          to_dict=lambda c: c.name,
          from_dict=lambda c: getattr(cosmo, c),
      )
  )

  Dictify.register_serializer(
      CustomSerializer(
          value_type=initial_mass_function.ImfBrokenPowerlaw,
          to_dict=lambda c: type(c).__name__,
          from_dict=lambda c: getattr(initial_mass_function, c)(),
      )
  )
