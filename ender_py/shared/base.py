# This is where I let ai take over, it works and nothing else god damn matters. I'm going to sleep.

import zstandard as zstd
from typing import Optional
import os


class Base440:
    def __init__(
        self,
        charset: Optional[str],
        use_compression: bool = True,
        compression_level: int = 3,
    ):
        """
        Initialize Base440 encoder/decoder with custom character set.

        Args:
            charset (str): 440-character string to use as alphabet.
                          If None, generates a default charset.
            use_compression (bool): Whether to use Zstandard compression
            compression_level (int): Zstandard compression level (1-22)
        """
        if charset is None:
            file = (
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                + "/unique.txt"
            )
            with open(file, "r", encoding="utf-8") as f:
                charset = f.read()
        if len(charset) != 440:
            raise ValueError(
                f"Charset must be exactly 440 characters, got {len(charset)}"
            )
        if len(set(charset)) != 440:
            raise ValueError("Charset must contain 440 unique characters")
        self.charset = charset

        # Create reverse mapping for decoding
        self.char_to_index = {char: i for i, char in enumerate(self.charset)}
        self.base = 440
        self.use_compression = use_compression

        # Initialize Zstandard compressor/decompressor
        if use_compression:
            self.compressor = zstd.ZstdCompressor(level=compression_level)
            self.decompressor = zstd.ZstdDecompressor()

    def encode(self, data: bytes) -> str:
        """
        Encode bytes to base440 string with optional compression.

        Args:
            data (bytes or str): Data to encode

        Returns:
            str: Base440 encoded string
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        if not data:
            return ""

        # Compress data if enabled
        if self.use_compression:
            data = self.compressor.compress(data)

        # Store original length to handle null bytes correctly
        original_len = len(data)

        # Convert bytes to a big integer
        num = int.from_bytes(data, byteorder="big")

        # Convert to base440
        if num == 0:
            # Handle zero case - encode the length to preserve null bytes
            return self._encode_length(original_len) + self.charset[0]

        result: list[str] = []
        while num > 0:
            result.append(self.charset[num % self.base])
            num //= self.base

        # Prepend length information to handle leading null bytes
        return self._encode_length(original_len) + "".join(reversed(result))

    def _encode_length(self, length: int) -> str:
        """Encode length as a small base440 prefix."""
        if length == 0:
            return self.charset[0] + ":"

        result: list[str] = []
        while length > 0:
            result.append(self.charset[length % self.base])
            length //= self.base

        return "".join(reversed(result)) + ":"

    def decode(self, encoded_str: str) -> bytes:
        """
        Decode base440 string back to bytes with optional decompression.

        Args:
            encoded_str (str): Base440 encoded string

        Returns:
            bytes: Decoded data
        """
        if not encoded_str:
            return b""

        # Split length prefix from data
        if ":" not in encoded_str:
            raise ValueError("Invalid encoded string format - missing length prefix")

        length_part, data_part = encoded_str.split(":", 1)

        # Decode length
        if not length_part:
            original_len = 0
        else:
            length_num = 0
            for char in length_part:
                if char not in self.char_to_index:
                    raise ValueError(f"Invalid character '{char}' in length prefix")
                length_num = length_num * self.base + self.char_to_index[char]
            original_len = length_num

        # Handle empty data case
        if not data_part or (len(data_part) == 1 and data_part == self.charset[0]):
            data = b"\x00" * original_len
        else:
            # Validate characters in data part
            for char in data_part:
                if char not in self.char_to_index:
                    raise ValueError(f"Invalid character '{char}' in encoded string")

            # Convert from base440 to integer
            num = 0
            for char in data_part:
                num = num * self.base + self.char_to_index[char]

            # Convert integer back to bytes with correct length
            if num == 0:
                data = b"\x00" * original_len
            else:
                # Calculate required bytes, then pad or truncate to original length
                required_bytes = (num.bit_length() + 7) // 8
                if required_bytes <= original_len:
                    # Pad with leading zeros if needed
                    data = num.to_bytes(original_len, byteorder="big")
                else:
                    # Use minimum required bytes if integer is larger than expected
                    data = num.to_bytes(required_bytes, byteorder="big")

        # Decompress if compression was used
        if self.use_compression and data:
            try:
                data = self.decompressor.decompress(data)
            except zstd.ZstdError:
                # If decompression fails, assume data wasn't compressed
                pass

        return data

    def encode_string(self, text: str) -> str:
        """Convenience method to encode a string and return string."""
        return self.encode(text.encode("utf-8"))

    def decode_string(self, encoded_str: str) -> str:
        """Convenience method to decode to string."""
        return self.decode(encoded_str).decode("utf-8")


# # Example usage and testing
# if __name__ == "__main__":
#     # Create encoder with compression enabled
#     encoder = Base440(
#         use_compression=True,
#         compression_level=3,
#         charset="!#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿŒœƒΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψωЀЁЂЃЄЇӜ†‡•‰‹›‼‽⁂⁅⁆ℓ℘ℜ™ℵℶℷℸ℺ℽℿ⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⅟ↂↃↄↅↆ↉←↑→↓↔↕↨⇐⇑⇒⇓⇔⇱⇲∀∂∃∏∑√∞∠∧∨∩∪∫∬∴∵∽≈≠≡≤≥⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡⊥⋅⌁⌂⌐⌖⌗⌘⌠⌡⎈⎋⎌⎔⎕⎰⎱⎴⏃⏄⏅⏆⏇⏈⏉⏊⏋⏌⏍⏎⏏═║╔╗╚╝╠╣╦╩╬▁▂▃▄▅▆▇▔▕▖▗▘▙▚▛▜▝▞▟◊◘◙◦★☆☢☣☮☯☺☻☼♀♂♠♡♢♣♤♥♦♧♩♪♫♬♭✓✔➴➵➶➷➸⟈⟉⦕⦖⧀⧁⧉⧓⧔⧕⧖⧗",
#     )
#     encoder_no_comp = Base440(
#         use_compression=False,
#         charset="!#$%&()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿŒœƒΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψωЀЁЂЃЄЇӜ†‡•‰‹›‼‽⁂⁅⁆ℓ℘ℜ™ℵℶℷℸ℺ℽℿ⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞⅟ↂↃↄↅↆ↉←↑→↓↔↕↨⇐⇑⇒⇓⇔⇱⇲∀∂∃∏∑√∞∠∧∨∩∪∫∬∴∵∽≈≠≡≤≥⊕⊖⊗⊘⊙⊚⊛⊜⊝⊞⊟⊠⊡⊥⋅⌁⌂⌐⌖⌗⌘⌠⌡⎈⎋⎌⎔⎕⎰⎱⎴⏃⏄⏅⏆⏇⏈⏉⏊⏋⏌⏍⏎⏏═║╔╗╚╝╠╣╦╩╬▁▂▃▄▅▆▇▔▕▖▗▘▙▚▛▜▝▞▟◊◘◙◦★☆☢☣☮☯☺☻☼♀♂♠♡♢♣♤♥♦♧♩♪♫♬♭✓✔➴➵➶➷➸⟈⟉⦕⦖⧀⧁⧉⧓⧔⧕⧖⧗",
#     )

#     # Test with various data types
#     test_cases = [
#         b"Hello, World!",
#         b"",
#         b"\x00",
#         b"\x00\x01\x02\x03\xff",
#         b"\x00\x00\x00\x00",
#         "Unicode test: 🌟🎉🚀".encode("utf-8"),
#         b"A" * 1000,  # Large repetitive data (good for compression)
#         "The quick brown fox jumps over the lazy dog. " * 50,  # Repetitive text
#         open(__file__, "rb").read() if __file__ else b"test code",  # This file
#     ]

#     print("Base440 Encoder/Decoder with Compression Test Results:")
#     print("=" * 80)

#     for i, original in enumerate(test_cases, 1):
#         if isinstance(original, str):
#             original = original.encode("utf-8")

#         print(f"\nTest Case {i}:")
#         print(f"Original: {original[:100]}{'...' if len(original) > 100 else ''}")
#         print(f"Original size: {len(original)} bytes")

#         # Test with compression
#         encoded_comp = encoder.encode(original)
#         decoded_comp = encoder.decode(encoded_comp)
#         comp_ratio = len(encoded_comp) / len(original) if len(original) > 0 else 0

#         # Test without compression
#         encoded_no_comp = encoder_no_comp.encode(original)
#         decoded_no_comp = encoder_no_comp.decode(encoded_no_comp)
#         no_comp_ratio = len(encoded_no_comp) / len(original) if len(original) > 0 else 0

#         print(f"Encoded (compressed): {len(encoded_comp)} chars")
#         print(f"Encoded (no compression): {len(encoded_no_comp)} chars")
#         print(f"Compression ratio: {comp_ratio:.3f}")
#         print(f"No compression ratio: {no_comp_ratio:.3f}")
#         print(
#             f"Compression benefit: {((no_comp_ratio - comp_ratio) / no_comp_ratio * 100) if no_comp_ratio > 0 else 0:.1f}%"
#         )

#         # Verify correctness
#         comp_match = original == decoded_comp
#         no_comp_match = original == decoded_no_comp

#         if comp_match and no_comp_match:
#             print("✅ Both methods successful!")
#         else:
#             print("❌ ERROR: Encoding/decoding failed!")
#             print(
#                 f"Original:                 {original[:100]}{'...' if len(original) > 100 else ''}"
#             )
#             print(
#                 f"Decoded (compressed):     {decoded_comp[:100]}{'...' if len(decoded_comp) > 100 else ''}"
#             )
#             print(
#                 f"Decoded (no compression): {decoded_no_comp[:100]}{'...' if len(decoded_no_comp) > 100 else ''}"
#             )
#             if not comp_match:
#                 print(
#                     f"   Compression mismatch: {len(original)} vs {len(decoded_comp)}"
#                 )
#             if not no_comp_match:
#                 print(
#                     f"   No compression mismatch: {len(original)} vs {len(decoded_no_comp)}"
#                 )

#     # Test string convenience methods
#     print(f"\n{'='*80}")
#     print("String Convenience Methods Test:")
#     test_string = "Hello, Base440 with compression! 🎯" * 10
#     encoded_str = encoder.encode_string(test_string)
#     decoded_str = encoder.decode_string(encoded_str)
#     ratio = len(encoded_str) / len(test_string)

#     print(f"Original: {test_string[:50]}...")
#     print(f"Original size: {len(test_string)} chars")
#     print(f"Encoded size: {len(encoded_str)} chars")
#     print(f"Ratio: {ratio:.3f}")
#     print(f"Match: {test_string == decoded_str}")

#     # Show charset info
#     print(f"\n{'='*80}")
#     print("Charset Information:")
#     print(f"First 50 chars: {encoder.charset[:50]}")
#     print(f"Last 50 chars: {encoder.charset[-50:]}")
#     print(f"Total charset length: {len(encoder.charset)}")
#     print(f"Compression enabled: {encoder.use_compression}")

#     # Special null byte test
#     print(f"\n{'='*80}")
#     print("Null Byte Handling Test:")
#     null_tests = [b"\x00", b"\x00\x00", b"\x00\x01\x00", b"hello\x00world"]
#     for null_data in null_tests:
#         encoded = encoder.encode(null_data)
#         decoded = encoder.decode(encoded)
#         print(
#             f"Original: {null_data} -> Encoded: {encoded} -> Decoded: {decoded} -> Match: {null_data == decoded}"
#         )
