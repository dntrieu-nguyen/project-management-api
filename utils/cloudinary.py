from cloudinary import CloudinaryImage


def uploadImg(file):
    CloudinaryImage(file).image(transformation=[
  { 'crop': "scale"},
  {'quality': "auto"},
  {'fetch_format': "auto"}
  ])
    return 