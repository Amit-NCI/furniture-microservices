"""Validated forms for the administrator management interface."""

from decimal import Decimal

from django import forms


class ManagementProductForm(forms.Form):
    """Validate product data before forwarding it to Product Service."""

    name = forms.CharField(
        max_length=255,
        strip=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Product name"}
        ),
    )

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Product description",
            }
        ),
    )

    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "0.01",
            }
        ),
    )

    image_url = forms.URLField(
        max_length=200,
        widget=forms.URLInput(
            attrs={"placeholder": "https://example.com/image.jpg"}
        ),
    )

    stock_quantity = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(
            attrs={
                "min": "0",
                "step": "1",
            }
        ),
    )

    def clean_image_url(self):
        """Allow only HTTP(S) product image URLs."""

        url = self.cleaned_data["image_url"]

        if not url.lower().startswith(("https://", "http://")):
            raise forms.ValidationError(
                "Image URL must use HTTP or HTTPS."
            )

        return url

    def to_api_payload(self):
        """Return JSON-compatible product fields after validation."""

        if not self.is_valid():
            raise ValueError("Cannot serialize invalid product data.")

        return {
            "name": self.cleaned_data["name"],
            "description": self.cleaned_data["description"],
            "price": str(self.cleaned_data["price"]),
            "image_url": self.cleaned_data["image_url"],
            "stock_quantity": self.cleaned_data["stock_quantity"],
        }
