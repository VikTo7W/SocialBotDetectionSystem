import torch
import numpy as np

def inspect_pt(path, max_print=5):
    obj = torch.load(path, map_location="cpu")
    print("Path:", path)
    print("Type:", type(obj))

    # Case 1: raw Tensor saved
    if torch.is_tensor(obj):
        t = obj
        print("Tensor dtype:", t.dtype)
        print("Tensor shape:", tuple(t.shape))

        # Basic stats
        if t.numel() > 0:
            t_min = t.min().item()
            t_max = t.max().item()
            print("min:", t_min, "max:", t_max)

        # Heuristics
        if t.dim() == 2:
            r, c = t.shape

            # Most common edge_index formats
            if r == 2 and c >= 1:
                E = c
                max_id = int(t.max().item())
                min_id = int(t.min().item())
                print(f"Looks like edge_index with shape [2, E]; E={E}")
                print("node_id range:", (min_id, max_id), "=> inferred num_nodes:", max_id + 1)
                print("First edges:", t[:, :max_print].T)

            elif c == 2 and r >= 1:
                E = r
                max_id = int(t.max().item())
                min_id = int(t.min().item())
                print(f"Looks like edge list with shape [E, 2]; E={E}")
                print("node_id range:", (min_id, max_id), "=> inferred num_nodes:", max_id + 1)
                print("First edges:", t[:max_print])

            else:
                print("2D tensor but not a standard edge_index/edge-list format.")
                print("Head:\n", t[:max_print])

        elif t.dim() == 1:
            n = t.shape[0]
            print(f"1D tensor length={n}")

            # If integer-like, could be edge_type or masks
            if t.dtype in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8, torch.bool):
                # sample unique values
                uniq = torch.unique(t[: min(n, 20000)]).cpu().numpy()
                uniq_small = uniq[:20]
                print("Unique (sampled) values:", uniq_small, ("..." if len(uniq) > 20 else ""))

                # If small set like {0,1,2} -> probably edge_type
                if len(uniq) <= 10 and set(uniq.tolist()).issubset(set(range(0, 10))):
                    print("Heuristic: could be edge_type (0..2) or a mask.")
                if set(uniq.tolist()).issubset({0, 1}) or t.dtype == torch.bool:
                    print("Heuristic: could be a train/val/test mask or binary labels.")
            else:
                print("Heuristic: could be edge weights or node features summary.")
                print("Head:", t[:max_print])

        else:
            print("Tensor has dim > 2; likely node features (x) or something else.")
            # show a small slice
            print("Slice:", t.flatten()[:max_print])

        return

    # Case 2: dict-like saved
    if isinstance(obj, dict):
        print("Dict keys:", list(obj.keys())[:40])
        for key in ["edge_index", "edge_type", "edge_weight", "num_nodes", "x", "y", "train_mask", "val_mask", "test_mask"]:
            if key in obj:
                v = obj[key]
                if torch.is_tensor(v):
                    print(f"{key}: tensor shape={tuple(v.shape)} dtype={v.dtype}")
                else:
                    print(f"{key}: {type(v)}")
        return

    # Case 3: PyG Data/HeteroData-like objects
    # (Your previous logic was fine; keep it minimal here)
    if hasattr(obj, "edge_index"):
        ei = obj.edge_index
        print("edge_index shape:", tuple(ei.shape))
        print("E:", ei.shape[1], "max node:", int(ei.max()), "inferred num_nodes:", int(ei.max()) + 1)
        return

    print("Unknown object format; you may need to print(obj) or check dataset code that saved it.")

# Example
inspect_pt("edge_type.pt")