"""Faces in photos: find them, describe each one as a vector, group the close ones.

Personal data (biometric): the vectors stay in the index under `/cache`, nothing is
ever sent anywhere. The only network access is the one-time download of the two
model files (`faces.weights`), which carries nothing about the photos.
"""

from __future__ import annotations
